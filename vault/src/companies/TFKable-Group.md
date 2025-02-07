```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "TFKable-Group" or company = "TFKable Group")
sort location, dt_announce desc
```
