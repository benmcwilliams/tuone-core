```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Optare-Group" or company = "Optare Group")
sort location, dt_announce desc
```
