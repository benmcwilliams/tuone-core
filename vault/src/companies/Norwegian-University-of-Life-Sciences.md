```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Norwegian-University-of-Life-Sciences" or company = "Norwegian University of Life Sciences")
sort location, dt_announce desc
```
