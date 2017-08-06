from OSC import OSCMessage
import argparse
import time
import sys
import itertools
import hoe.osc_utils as osc_utils


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--filename')
    parser.add_argument('--host')
    parser.add_argument('--port')
    args = parser.parse_args()

    host = args.host
    port = int(args.port)
    filename = args.filename
    play_lidar(filename, host, port)


def play_lidar(filename, host="127.0.0.1", port=7000):
    client = osc_utils.get_osc_client(host=host, port=port)

    f = None
    try:
        with open(filename, 'r') as f:
            data = [(t, __build_msg(args)) for t, args in map(eval, f.readlines())]
    except Exception:
        print "Unable to load file", filename
        return
    finally:
        if f is not None:
            f.close()

    print "Parsed data of length", len(data)

    total_time = data[-1][0] - data[0][0]
    mps = len(data) / total_time
    spm = 1 / mps
    start_time = time.time()
    print "Beginning feed of %s messages/second over %s seconds" % (mps, total_time)
    for i, data in enumerate(data):
        client.send(data[1])
        sleep_time = (start_time + i * spm) - time.time()
        time.sleep(max(0, sleep_time))

    finish_time = time.time()
    print "Finished at time", finish_time, "Took total time:", finish_time - start_time


def __pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return itertools.izip(a, b)


def __build_msg(args):
    msg = OSCMessage(args[0])
    data = args[2]
    msg.append(int(data[0]), typehint='i')
    for d in data[1:]:
        msg.append(float(d), typehint='f')

    return msg


if __name__ == '__main__':
    sys.exit(main())
