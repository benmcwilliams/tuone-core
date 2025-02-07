```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Jifmar-Offshore-Services" or company = "Jifmar Offshore Services")
sort location, dt_announce desc
```
