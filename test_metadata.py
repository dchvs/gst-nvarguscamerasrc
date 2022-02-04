#!/usr/bin/python3

from argparse import ArgumentParser
import os
import time

from gi.repository import Gst
from gi.repository import GObject

SECONDS_TO_NANOSECONDS = 1000000000
TIMEOUT_NS = 2 * SECONDS_TO_NANOSECONDS

desc = "nvarguscamerasrc name=nvarguscamerasrc ! appsink emit-signals=true name=appsink "

class GStreamerMasterError(RuntimeError):
        pass

class UserAppsinkBuffersCallback:
        def __init__(self):
                pass

        def __call__(self, buffer):
                timestamp_meta = buffer.get_reference_timestamp_meta(Gst.Caps.from_string("timestamp/roboticsresearch"))

                print ("AppSink buffer timestamp metadata: timestamp => ", timestamp_meta.timestamp)

class UserPadProbeBuffersCallback:
        def __init__(self):
                pass

        def __call__(self, buffer):
                timestamp_meta = buffer.get_reference_timestamp_meta(Gst.Caps.from_string("timestamp/roboticsresearch"))

                print("PadProbe buffer timestamp metadata: timestamp => ", timestamp_meta.timestamp)


class GStreamerMaster:
        def __init__(self):
                Gst.init(None)
                GObject.MainLoop()
                self.pipeline = None

        def create_pipe(self, desc):
                try:
                        self.pipeline = Gst.parse_launch(desc)
                except glib.GError as e:
                        raise GStreamerMasterError("Unable to create the media") from e

        def start(self):
                ret = self.pipeline.set_state(Gst.State.PLAYING)
                if Gst.StateChangeReturn.FAILURE == ret:
                        raise GStreamerMasterError("Unable to start the media") from e

        def stop(self):
                ret, current, pending = self.pipeline.get_state(gst.CLOCK_TIME_NONE)
                if Gst.State.PLAYING == current:
                        self.pipeline.send_event(gst.Event.new_eos())
                        self.pipeline.get_bus().timed_pop_filtered(TIMEOUT_NS, gst.MessageType.EOS)
                        ret = self.pipeline.set_state(Gst.State.NULL)
                        if gst.StateChangeReturn.FAILURE == ret:
                                raise GStreamerMasterError("Unable to stop the media") from e

        def get_element(self, element):
                return self.pipeline.get_by_name(element)

class AppsinkMaster():
        def __init__(self, Appsink, user_buffer_callback):
                self.AppsinkObj = Appsink
                self.buffer_callback = user_buffer_callback

                self.__get_buffer()

        def __get_buffer(self):
                try:
                        self.AppsinkObj.connect("new-sample", self._get_buffer, self.AppsinkObj)
                except AttributeError as e:
                        raise GStreamerMasterError("Unable to install buffers callback") from e

        def _get_buffer(self, AppsinkObj, data):
                sample = AppsinkObj.emit("pull-sample")
                buffer = sample.get_buffer()

                # Pass the buffers
                if self.buffer_callback is not None:
                        self.buffer_callback(buffer)

                return Gst.FlowReturn.OK


class PadProbeMaster():
        def __init__(self, PadProbe, user_buffer_callback):
                self.PadProbe = PadProbe
                self.buffer_callback = user_buffer_callback

                self.__get_buffer()

        def __get_buffer(self):
                src_pad = self.PadProbe.get_static_pad("src")
                probe_id = src_pad.add_probe(Gst.PadProbeType.BUFFER, self._get_buffer)

        def _get_buffer(self, pad, info):
                buffer = info.get_buffer()

                # Pass the buffers
                if self.buffer_callback is not None:
                        self.buffer_callback(buffer)

                return Gst.PadProbeReturn.OK

class App():
        def __init__(self):
                self.gstreamer_master = None
                self.appsink_master = None
                self.pad_probe_master = None

                self.setup()

        def setup(self):
                self.gstreamer_master = GStreamerMaster ()
                self.gstreamer_master.create_pipe(desc)

                self.user_appsink_buffer_callback = UserAppsinkBuffersCallback()
                self.user_padprobe_buffer_callback = UserPadProbeBuffersCallback()

        def run(self):
                self.gstreamer_master.start()

                self.appsink_master = AppsinkMaster(self.gstreamer_master.get_element("appsink"), self.user_appsink_buffer_callback)

                self.pad_probe_master = PadProbeMaster(self.gstreamer_master.get_element("nvarguscamerasrc"), self.user_padprobe_buffer_callback)

                time.sleep(3)

        def stop(self):
                self.gstreamer_master.stop()


def _parse_args():
        parser = ArgumentParser(
                description="Example app to retrieve timestamp metadata from buffers via Appsink & PadProbes")
        parser.add_argument('--verbose', action='count', help='Print GStreamer log')

        return parser.parse_args()

if __name__ == '__main__':
        args = _parse_args()
        if args.verbose:
                os.environ['GST_DEBUG'] = 'GST_PIPELINE:INFO,1'

        app = App()
        try:
                app.run()
                print("Running the app...")
        except KeyboardInterupt:
                print("Cleanning up")
                app.stop()
