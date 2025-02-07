```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "MVM-Group" or company = "MVM Group")
sort location, dt_announce desc
```
