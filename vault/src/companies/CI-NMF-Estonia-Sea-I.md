```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "CI-NMF-Estonia-Sea-I" or company = "CI NMF Estonia Sea I")
sort location, dt_announce desc
```
