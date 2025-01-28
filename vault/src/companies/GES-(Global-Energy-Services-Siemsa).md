```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "GES-(Global-Energy-Services-Siemsa)" or company = "GES (Global Energy Services Siemsa)")
sort location, dt_announce desc
```
