```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and company = "Institute of Energy and Climate Research IEK 5 Photovoltaik"
sort location, dt_announce desc
```
