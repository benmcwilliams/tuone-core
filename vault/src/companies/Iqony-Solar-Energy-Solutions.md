```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Iqony-Solar-Energy-Solutions" or company = "Iqony Solar Energy Solutions")
sort location, dt_announce desc
```
