#!/usr/bin/python3

import time

from gi.repository import Gst
from gi.repository import GObject

desc = "nvarguscamerasrc name=nvarguscamerasrc ! appsink emit-signals=true name=appsink "

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

                print ("AppSink buffer timestamp metadata: timestamp => ", timestamp_meta.timestamp)


class PadProbeMaster():
        def __init__(self):
                pass
        def get_buffer(self, probe):
                src_pad = probe.get_static_pad("src")
                probe_id = src_pad.add_probe(Gst.PadProbeType.BUFFER, self.probe_callback)

        def probe_callback(self, pad, info):
                buffer = info.get_buffer()
                timestamp_meta = buffer.get_reference_timestamp_meta(Gst.Caps.from_string("timestamp/roboticsresearch"))

                print("PadProbe buffer timestamp metadata: timestamp => ", timestamp_meta.timestamp)

                return Gst.PadProbeReturn.OK



GObject.MainLoop()
m = GStreamerMaster ()
m.create_pipe(desc)
m.start()

appsink_master = AppsinkMaster()
appsink_master.get_buffer(m.get_element("appsink"))

pad_probe_master = PadProbeMaster()
pad_probe_master.get_buffer(m.get_element("nvarguscamerasrc"))

time.sleep(3)
