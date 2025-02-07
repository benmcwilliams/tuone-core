```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Velux-Group" or company = "Velux Group")
sort location, dt_announce desc
```
