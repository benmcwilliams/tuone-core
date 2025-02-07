```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "GRTgaz-Deutschland" or company = "GRTgaz Deutschland")
sort location, dt_announce desc
```
