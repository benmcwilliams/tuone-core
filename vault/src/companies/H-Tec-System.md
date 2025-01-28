```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "H-Tec-System" or company = "H Tec System")
sort location, dt_announce desc
```
