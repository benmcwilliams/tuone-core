```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "HH-WIN" or company = "HH WIN")
sort location, dt_announce desc
```
