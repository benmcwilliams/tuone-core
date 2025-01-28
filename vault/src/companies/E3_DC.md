```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "E3_DC" or company = "E3_DC")
sort location, dt_announce desc
```
