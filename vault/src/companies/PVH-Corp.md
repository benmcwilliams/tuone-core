```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "PVH-Corp" or company = "PVH Corp")
sort location, dt_announce desc
```
