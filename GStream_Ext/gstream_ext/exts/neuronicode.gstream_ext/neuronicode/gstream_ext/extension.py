import asyncio
import omni.ext
import omni.ui as ui
from . import omni_gstream
from .omni_gstream import OmniGstream as OGst
from . import frame_capture_test as fct




# Functions and vars are available to other extension as usual in python: `example.python_ext.some_public_function(x)`
def some_public_function(x: int):
    print("[neuronicode.gstream_ext] some_public_function was called with x: ", x)
    return x ** x


# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class NeuronicodeGstream_extExtension(omni.ext.IExt):
    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    
    def on_startup(self, ext_id):
        print("[neuronicode.gstream_ext] neuronicode gstream_ext startup")

        self._count = 0
        self.omni_gstream: OGst = None  # Initialize here

        self._window = ui.Window("Gstream Ext", width=300, height=300)
        with self._window.frame:
            with ui.VStack():
                label = ui.Label("")


                def on_click():
                    if not self.omni_gstream:
                        self.omni_gstream = OGst()
                    
                    
                    return

                def on_reset():
                    asyncio.ensure_future(self.omni_gstream.push_one_frame())
                    return

                with ui.HStack():
                    ui.Button("Init", clicked_fn=on_click)
                    ui.Button("Run", clicked_fn=on_reset)

    def on_shutdown(self):
        print("[neuronicode.gstream_ext] neuronicode gstream_ext shutdown")
        if self.omni_gstream:  # Ensure to stop the coroutine if it's running
            self.omni_gstream.clean_tasks()  # Ensure this method exists in your OmniGstream class
            self.omni_gstream = None  # Clean up reference
        else:
            print("Instance not found")

