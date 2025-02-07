```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Kion-Group" or company = "Kion Group")
sort location, dt_announce desc
```
