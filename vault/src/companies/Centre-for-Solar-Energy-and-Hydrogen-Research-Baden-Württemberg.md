```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and company = "Centre for Solar Energy and Hydrogen Research Baden Württemberg"
sort location, dt_announce desc
```
