# SNARS ZTM Parser

## Instructions:

The file [`parser.py`](parser.py) contains the `ZTMReader` class which is used to read and parse the ZTM timetable data.

After reading (invoking the `.read()` method) the class has the following important properties:

- `stops` - a `dict` of `dict`s describing stops, they keys are the 6-digit bus stop codes (stored as `str`, not `int`). The keys and values of each inner `dict` are:
    - `id: str` - the 6-digit bus stop code
    - `group_name: str` - the name of the group to which the bus stop belongs (these are the usual known bus stop names)
    - `street: str` - the name of the street on which the bus stop is located.
    - `lat: float` - the lattitude of the bus stop (in degrees north)
    - `long: float` - the longitude of the bus stop (in degrees east)
- `edges` - a `list` of `dict`s describing connections between bus stops. The keys and values of each dict are:
    - `route: str` - a unique identifier of the route
    - `from: str` - the id of the bus stop from which the edge starts
    - `to: str` - the id of the  bus sto at which the edge ends
    - `start_time: int` - the time of departure from the starting bus stop in minutes from midnight
    - `end_time: int` - the time of departure from the ending bus stop in minutes from midnight
    - `time_between: int` - time required to travel this edge in minutes
    - `type: str` - route type, I don't know what this is but it was in the data.

**Important: the edge between the same two bus stops appears multiple times in the `edges` list - once for each bus that travels between two stops. You need to remove them before drawing the graph. The `create_simple_edgelist()` method creates an edge list without duplicates.**

## Example

```python
from parser import ZTMReader
import networkx as nx

reader = ZTMReader("path/to/timetable/file.TXT")
reader.read()

edgelist = reader.create_simple_edgelist()

G = nx.DiGraph()
G.add_edges_from(edgelist)
```
