```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Greenrail-Group" or company = "Greenrail Group")
sort location, dt_announce desc
```
