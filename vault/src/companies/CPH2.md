```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "CPH2" or company = "CPH2")
sort location, dt_announce desc
```
