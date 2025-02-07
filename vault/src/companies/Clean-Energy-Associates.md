```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Clean-Energy-Associates" or company = "Clean Energy Associates")
sort location, dt_announce desc
```
