```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "phases"
where reject-phase = false and company = "Center for Solar Energy and Hydrogen Research Baden Württemberg (ZSW)"
sort location, dt_announce desc
```
