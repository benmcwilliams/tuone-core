```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "London-Taxi-Corporation" or company = "London Taxi Corporation")
sort location, dt_announce desc
```
