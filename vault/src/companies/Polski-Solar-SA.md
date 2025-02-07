```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Polski-Solar-SA" or company = "Polski Solar SA")
sort location, dt_announce desc
```
