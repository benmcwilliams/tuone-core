```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Good-Energy-Group" or company = "Good Energy Group")
sort location, dt_announce desc
```
