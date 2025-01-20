```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and company = "Westmill Solar Co operative"
sort location, dt_announce desc
```
