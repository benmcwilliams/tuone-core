```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Brandenburg-University-of-Technology-Cottbus-Senftenberg-(BTU)" or company = "Brandenburg University of Technology Cottbus Senftenberg (BTU)")
sort location, dt_announce desc
```
