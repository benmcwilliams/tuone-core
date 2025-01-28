```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Fred.-Olsen-Windcarrier" or company = "Fred. Olsen Windcarrier")
sort location, dt_announce desc
```
