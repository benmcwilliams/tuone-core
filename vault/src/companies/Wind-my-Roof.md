```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Wind-my-Roof" or company = "Wind my Roof")
sort location, dt_announce desc
```
