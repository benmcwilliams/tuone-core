```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Maple-Power" or company = "Maple Power")
sort location, dt_announce desc
```
