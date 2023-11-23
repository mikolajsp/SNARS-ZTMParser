from __future__ import annotations
from typing import Callable, Sequence, Iterator, Dict, Set
import re

import networkx as nx
import matplotlib.pyplot as plt


class ZTMIterator:
    def __init__(self, iterator: Iterator, tag: str):
        """
        Initializes a ZTM Iterator for a given iterator () and tag.
        """
        self.__iter = iterator
        self.__start = "*" + tag
        self.__end = "#" + tag

    @classmethod
    def iterate(cls, iterator: Iterator, tag: str) -> ZTMIterator:
        return ZTMIterator(iterator, tag)

    def run(self, func: Callable) -> None:
        """
        Runs a supplied function for lines between the start and end tags.

        Args:
            func: function to run. It has to take `Sequence[str]` as an argument and return `None` (the output of func is not saved).
        """
        # initialize array of lines, and a flag
        lines = []
        inside_tag = False

        while True:
            line = self.__iter.__next__().strip()

            # set flag if start tag is found, this is the interesting part
            if line.startswith(self.__start):
                inside_tag = True
                continue
            # call the function if tag ended
            elif line.startswith(self.__end):
                func(lines)
                return

            if inside_tag:
                lines.append(line)


class ZTMReader:
    def __init__(self, file_name: str):
        self.file_name = file_name
        self.stop_groups = {}
        self.stops = {}
        self.edges = []
        self.is_read = False

    def read(self) -> None:
        # first pass to get busstop group names
        with open(self.file_name, "r", encoding="windows-1250") as input_file:
            iterator = input_file.__iter__()
            ZTMIterator.iterate(iterator, "ZP").run(self.read_busstop_group_names)

        # second pass to get busstop data (nodes of the graph)
        with open(self.file_name, "r", encoding="windows-1250") as input_file:
            iterator = input_file.__iter__()
            ZTMIterator.iterate(iterator, "ZP").run(self.read_busstop_groups)

        # third pass to get routes (edges of the graph)
        with open(self.file_name, "r", encoding="windows-1250") as input_file:
            iterator = input_file.__iter__()
            try:
                # this loop runs once for each route (bus line, tram line etc.)
                while True:
                    ZTMIterator.iterate(iterator, "WK").run(self.read_routes)
            except StopIteration:
                self.is_read = True
                return
        self.is_read = True

    def read_busstop_groups(self, lines: Sequence[str]) -> None:
        try:
            iterator = lines.__iter__()
            # this loop runs once for each busstop group
            while True:
                ZTMIterator.iterate(iterator, "PR").run(self.read_busstops)
        # when we get to the end of the file without finding the PR tag, StopIteration is raised
        except StopIteration:
            return

    def read_busstop_group_names(self, lines: Sequence[str]) -> None:
        for line in lines:
            # busstop group names are defined on lines starting with 4 digits
            if re.match(r"\d{4}\s", line):
                busstop_group_info = re.split(r"\s{2,}", line)
                busstop_group_id = int(busstop_group_info[0])
                busstop_group_name = busstop_group_info[1].strip(",")

                self.stop_groups[busstop_group_id] = busstop_group_name

    def read_busstops(self, lines: Sequence[str]) -> None:
        for line in lines:
            # bus stops are defined on lines starting with 6 digits
            if re.match(r"\d{6}\s", line):
                # bus stop data is separated by 2 or more spaces
                busstop_info = re.split(r"\s{2,}", line)
                self.parse_busstop(busstop_info)

    def parse_busstop(self, busstop_info: Sequence[str]) -> None:
        busstop_id = busstop_info[0]
        busstop_street = busstop_info[2].strip(",")

        lat = re.findall(r"\d+\.\d+", busstop_info[4])
        long = re.findall(r"\d+\.\d+", busstop_info[5])

        lat = float(lat[0]) if lat else None
        long = float(long[0]) if long else None
        group_id = int(busstop_id[0:4])

        busstop = {
            "id": busstop_id,
            "group_name": self.stop_groups[group_id],
            "street": busstop_street,
            "lat": lat,
            "long": long,
        }
        self.stops[busstop_id] = busstop

    def _parse_time(self, time: str) -> int:
        """
        Parses a time string in the format HH.MM to minutes from midnight.
        """
        time_parts = time.split(".")
        hours = int(time_parts[0])
        minutes = int(time_parts[1])
        return (hours * 60 + minutes) % 1440

    def read_routes(self, lines: Sequence[str]) -> None:
        last_stop = None
        last_time = None
        this_route = None

        for line in lines:
            route_info = line.split()
            route = route_info[0]
            stop = route_info[1]
            route_type = route_info[2]
            time = self._parse_time(route_info[3])

            # this is the first stop of the route
            # we DON'T add this yet, as we add edges,
            # the edge will be added with the next stop
            if (
                this_route is None
                or last_stop is None
                or last_time is None
                or route != this_route
            ):
                this_route = route
            else:
                self.add_edge(route, last_stop, last_time, stop, time, route_type)

            last_stop = stop
            last_time = time

    def add_edge(
        self,
        route: str,
        start_stop: str,
        start_time: int,
        end_stop: str,
        end_time: int,
        route_type: str,
    ):
        time_delta = end_time - start_time
        self.edges.append(
            {
                "route": route,
                "from": start_stop,
                "to": end_stop,
                "start_time": start_time,
                "end_time": end_time,
                "time_between": time_delta,
                "type": route_type,
            }
        )

    def create_simple_edgelist(self) -> Sequence[Sequence]:
        """
        Creates an unweighted, directed edgelist without duplicate edges.
        """
        if not self.is_read:
            raise Exception(
                "The file has not been read and parsed yet. Please run read() first."
            )

        edgelist = set()
        for edge in self.edges:
            edge_tuple = (edge["from"], edge["to"])
            edgelist.add(edge_tuple)

        return list(edgelist)


if __name__ == "__main__":
    reader = ZTMReader("Lab8/data/RA231125.TXT")
    reader.read()

    for i, stop in enumerate(reader.stops.values()):
        print(stop)
        if i > 10:
            break

    for i, edge in enumerate(reader.edges):
        print(edge)
        if i > 10:
            break
