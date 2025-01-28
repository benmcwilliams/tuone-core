```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Nervion-Naval-Offshore" or company = "Nervion Naval Offshore")
sort location, dt_announce desc
```
