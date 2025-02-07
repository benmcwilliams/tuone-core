```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Catalan-Institute-of-Nanoscience-and-Nanotechnology" or company = "Catalan Institute of Nanoscience and Nanotechnology")
sort location, dt_announce desc
```
