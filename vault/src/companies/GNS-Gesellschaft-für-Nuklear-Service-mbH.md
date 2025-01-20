```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and company = "GNS Gesellschaft für Nuklear Service mbH"
sort location, dt_announce desc
```
