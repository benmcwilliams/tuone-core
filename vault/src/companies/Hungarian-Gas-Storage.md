```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Hungarian-Gas-Storage" or company = "Hungarian Gas Storage")
sort location, dt_announce desc
```
