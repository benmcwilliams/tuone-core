```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Belgian-government" or company = "Belgian government")
sort location, dt_announce desc
```
