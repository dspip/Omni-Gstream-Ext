import asyncio
import threading # type: ignore
import time  # type: ignore
import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib
import numpy as np
import ctypes
from omni.kit.widget.viewport.capture import ByteCapture
from omni.kit.viewport.utility import get_active_viewport
import omni.kit.async_engine
from functools import partial  # type: ignore
import carb  # Importing carb for logging

class OmniGstream:
    def __init__(self):
        self.fps = 30
        self.appsrc = None
        self.pipeline = None
        self.glib_loop = None
        self.gst_thread = None
        self.capture_task = None
        self.viewport_api = get_active_viewport()
        carb.log_info("Initializing OmniGstream")
        self.gst_init()
        self.start_thread_loop()
        self.start_frame_loop() # Commit this if you want to push frames manualy from other loop
        
        
    def gst_init(self):
        
        # Get viewport settings
        if self.viewport_api:
            vp_res = self.viewport_api.resolution
            width, height = vp_res[0], vp_res[1] 
            
        else:
            carb.log_error("No viewport found")
            self.clean_tasks()
            return
        
        # Initialize GStreamer
        Gst.init(None)  

        self.appsrc = Gst.ElementFactory.make("appsrc", "video_source")
        if self.appsrc is None:
            carb.log_error("Error: appsrc could not be created. Check GStreamer installation.")
            return

        # Create GStreamer pipeline
        self.pipeline = Gst.parse_launch(
            "appsrc name=src ! videoconvert ! x264enc speed-preset=veryfast tune=zerolatency bitrate=5000 ! h264parse config-interval=-1 ! rtph264pay ! udpsink host=127.0.0.1 port=5000"
        )

        self.appsrc = self.pipeline.get_by_name("src")
        
        self.appsrc.set_property("caps", Gst.Caps.from_string(f"video/x-raw,format=RGBA,width={width},height={height},framerate={self.fps}/1"))
        self.appsrc.set_property("format", Gst.Format.TIME)

        self.pipeline.set_state(Gst.State.PLAYING)
        carb.log_info("GStreamer initialized and pipeline is playing.")
        
        return self.appsrc

    async def capture_frame(self):
        capture_callback = partial(self.on_capture_completed, self=self)
        self.viewport_api.schedule_capture(ByteCapture(capture_callback))
        
    @staticmethod
    def on_capture_completed(capsule, image_size, width, height, format, self):
        try:
            ctypes.pythonapi.PyCapsule_GetPointer.restype = ctypes.POINTER(ctypes.c_byte * image_size)
            ctypes.pythonapi.PyCapsule_GetPointer.argtypes = [ctypes.py_object, ctypes.c_char_p]
            content = ctypes.pythonapi.PyCapsule_GetPointer(capsule, None)
        except Exception as e:
            carb.log_error(f"[XXX] Failed to get capture buffer: {e}")
            return

        pointer = ctypes.cast(content, ctypes.POINTER(ctypes.c_byte * image_size))
        np_arr = np.frombuffer(pointer.contents)
        self.push_frame(np_arr)

    def push_frame(self, frame):
        if self.appsrc is None:
            return False
        
        if frame is None:
            carb.log_error("Failed to capture frame.")
            return False

        # Create a GStreamer buffer from the frame data
        buffer = Gst.Buffer.new_allocate(None, frame.nbytes, None)
        buffer.fill(0, frame.tobytes())

        # Push the buffer to the pipeline
        retval = self.appsrc.emit("push-buffer", buffer)
        if retval != Gst.FlowReturn.OK:
            carb.log_error("Failed to push buffer to pipeline.")
            return False

        return True

    async def frame_push_loop(self):
        target_frame_time = 1.0 / self.fps
        last_time = time.time()

        while True:
            current_time = time.time()
            delta_time = current_time - last_time 
            
            if delta_time >= target_frame_time:
                await self.capture_frame()  
                print(time.time())
                last_time = current_time 

            # Optionally yield control to allow other tasks to run, 
            # but you can also use a small sleep to prevent busy waiting.
            await asyncio.sleep(0.01)  # Yield control back to the event loop
            
    def start_thread_loop(self):
        self.loop = GLib.MainLoop()    
        try:
            self.thread = threading.Thread(target=self.loop.run)
            self.thread.start()
            carb.log_info("GStreamer thread started.")
        except Exception as ex:
            carb.log_error(f"Error starting GStreamer thread: {ex}")
        
    def start_frame_loop(self):
        self.capture_task = omni.kit.async_engine.run_coroutine(self.frame_push_loop())
        return self.capture_task
    
    def stop_frame_loop(self):
        self.capture_task.cancel()

    def clean_tasks(self):
        carb.log_info("Cleaning up OGst resources...")
        
        # Stop frame capture loop
        if self.capture_task and not self.capture_task.done():
            self.capture_task.cancel()
            self.capture_task = None
        
        # Stop Glib main loop
        if self.glib_loop:
            self.glib_loop.quit()  # Stop the main loop
            self.thread.join()  # Wait for the thread to finish
            self.glib_loop = None  # Clean up the loop reference
            self.thread = None  # Clean up the thread reference
            carb.log_info("GStreamer thread stopped.")
            
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)  # Stop the pipeline
            self.pipeline = None  # Release the reference
        self.appsrc = None  # Release appsrc reference
