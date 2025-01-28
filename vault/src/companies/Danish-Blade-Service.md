```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Danish-Blade-Service" or company = "Danish Blade Service")
sort location, dt_announce desc
```
