```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Ardagh-Group" or company = "Ardagh Group")
sort location, dt_announce desc
```
