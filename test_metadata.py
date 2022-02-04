#!/usr/bin/python3

from gi.repository import Gst
from gi.repository import GObject

desc0 = "videotestsrc ! appsink emit-signals=true name=appsink "
desc = "nvarguscamerasrc ! appsink emit-signals=true name=appsink "

class BufferingMaster:
        pass


class GStreamerMaster:
        def __init__(self):
                Gst.init(None)
                self.pipeline = None

        def create_pipe(self, desc):
                self.pipeline = Gst.parse_launch(desc)

        def start(self):
                self.pipeline.set_state(Gst.State.PLAYING)

        def stop(self):
                self.pipeline.set_state(Gst.State.NULL)

        def get_element(self, element):
                return self.pipeline.get_by_name(element)

class AppsinkMaster:
        def __init__(self):
                pass
        def get_buffer(self, appsink):
                sample = appsink.emit("pull-sample")
                buffer = sample.get_buffer()

                timestamp_meta = buffer.get_reference_timestamp_meta(Gst.Caps.from_string("timestamp/roboticsresearch"))

                print ("\nAppSink buffer timestamp metadata: timestamp => ", timestamp_meta.timestamp, "\n")


GObject.MainLoop()
m = GStreamerMaster ()
m.create_pipe(desc)
m.start()

appsink_master = AppsinkMaster()
appsink_master.get_buffer(m.get_element("appsink"))
