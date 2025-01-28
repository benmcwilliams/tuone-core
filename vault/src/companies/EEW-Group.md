```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "EEW-Group" or company = "EEW Group")
sort location, dt_announce desc
```
