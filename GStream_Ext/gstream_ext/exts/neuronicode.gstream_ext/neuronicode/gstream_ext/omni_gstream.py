import asyncio
import threading # type: ignore
import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib
import numpy as np
import ctypes
from omni.kit.widget.viewport.capture import ByteCapture
from omni.kit.viewport.utility import get_active_viewport
import omni.kit.async_engine
from functools import partial # type: ignore


class OmniGstream:
    def __init__(self):
        self.appsrc = None
        self.pipeline = None
        self.glib_loop = None
        self.thread = None
        self.capture_task = None
        self.viewport_api = get_active_viewport()
        print("Init OGst")
        self.gst_init()
        self.start_thread_loop()
        self.start_frame_loop()
        
    def gst_init(self):

        Gst.init(None)  # Initialize GStreamer

        self.appsrc = Gst.ElementFactory.make("appsrc", "video_source")
        if self.appsrc is None:
            print("Error: appsrc could not be created. Check GStreamer installation.")

        self.pipeline = Gst.parse_launch(
            "appsrc name=src ! videoconvert ! x264enc speed-preset=ultrafast tune=zerolatency key-int-max=25 ! h264parse config-interval=-1 ! rtph264pay ! udpsink host=127.0.0.1 port=5000"
        )

        self.appsrc = self.pipeline.get_by_name("src")

        width, height = 1920, 1080 
        fps = 30
        self.appsrc.set_property("caps", Gst.Caps.from_string(f"video/x-raw,format=RGBA,width={width},height={height},framerate={fps}/1"))
        self.appsrc.set_property("format", Gst.Format.TIME)

        self.pipeline.set_state(Gst.State.PLAYING)
        
        return self.appsrc

    async def capture_frame(self):
        print(f'Viewport: {self.viewport_api}, Scheduling frame capture...')  # Debugging line
        # capture = self.viewport_api.schedule_capture(ByteCapture(self.on_capture_completed))
        capture_callback = partial(self.on_capture_completed, self=self)
        capture = self.viewport_api.schedule_capture(ByteCapture(capture_callback))
        # captured_aovs = await capture.wait_for_result()
        # if captured_aovs:
        #     print(f'AOV "{captured_aovs[0]}"')
        # else:
        #     print(f'No image was written')
        
    @staticmethod
    def on_capture_completed(capsule, image_size, width, height, format, self):
        print("on capture complete")
        try:
            ctypes.pythonapi.PyCapsule_GetPointer.restype = ctypes.POINTER(ctypes.c_byte * image_size)
            ctypes.pythonapi.PyCapsule_GetPointer.argtypes = [ctypes.py_object, ctypes.c_char_p]
            content = ctypes.pythonapi.PyCapsule_GetPointer(capsule, None)
        except Exception as e:
            print(f"[XXX] Failed to get capture buffer: {e}")
            return

        pointer = ctypes.cast(content, ctypes.POINTER(ctypes.c_byte * image_size))
        np_arr = np.frombuffer(pointer.contents)
        # print(np_arr[0:10][0:10][0:10])
        self.push_frame(np_arr)

    def push_frame(self, frame):
        if frame is None:
            print("Failed to capture frame.")
            return False

        # Create a GStreamer buffer from the frame data
        buffer = Gst.Buffer.new_allocate(None, frame.nbytes, None)
        buffer.fill(0, frame.tobytes())

        # Push the buffer to the pipeline
        retval = self.appsrc.emit("push-buffer", buffer)
        if retval != Gst.FlowReturn.OK:
            print("Failed to push buffer to pipeline.")
            return False

        return True
    
    async def frame_push_loop(self):
        frame_duration = 1.0 / 60.0  # Duration for each frame in seconds (30 FPS)
        while True:  
            print("Main loop")
            await self.capture_frame()
            await asyncio.sleep(frame_duration)  # Non-blocking wait for 1/30 seconds
            
    async def push_one_frame(self):
        await self.capture_frame()
    
    def start_thread_loop(self):
        self.loop = GLib.MainLoop()    
        try:
            self.thread = threading.Thread(target=self.loop.run)
            self.thread.start()
            print("thread started:")
        except Exception as ex:
            pass
        
    def start_frame_loop(self):
        self.capture_task = omni.kit.async_engine.run_coroutine(self.frame_push_loop())
        return self.capture_task
    
    def stop_frame_loop(self):
        self.capture_task.cancel()

                
    def clean_tasks(self):
        print("Cleaning up OGst resources...")
        
        # Stop frame capture loop
        if self.capture_task and not self.capture_task.done():
            self.capture_task.cancel()
            self.capture_task = None
        
        # Stop Glib main loop loop 
        if self.glib_loop:
            self.glib_loop.quit()  # Stop the main loop
            self.thread.join()  # Wait for the thread to finish
            self.glib_loop = None  # Clean up the loop reference
            self.thread = None  # Clean up the thread reference
            print("Thread stopped.")
            
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)  # Stop the pipeline
            self.pipeline = None  # Release the reference
        self.appsrc = None  # Release appsrc reference
        
