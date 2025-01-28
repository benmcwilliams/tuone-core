```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "MBS-Consulting---Cerved-Group" or company = "MBS Consulting   Cerved Group")
sort location, dt_announce desc
```
