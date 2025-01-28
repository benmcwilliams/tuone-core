```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "China-Resources-Group" or company = "China Resources Group")
sort location, dt_announce desc
```
