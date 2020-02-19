import argparse

from pyknp_eventgraph import EventGraph


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('IN', help='path to EventGraph')
    parser.add_argument('--binary', action='store_true', help='whether the input is binary')
    args = parser.parse_args()

    if args.binary:
        f = open(args.IN, 'rb')
    else:
        f = open(args.IN, 'r', encoding='utf-8', errors='ignore')

    evg = EventGraph.load(f, binary=args.binary, logging_level='DEBUG')

    print('# events:', len(evg.events))
    for event in evg.events[:5]:
        print('Event #%d:' % event.evid, event.surf)

    f.close()


if __name__ == '__main__':
    main()
