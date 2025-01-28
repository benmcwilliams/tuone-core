```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Organic-Electronics-Technologies-(OET)" or company = "Organic Electronics Technologies (OET)")
sort location, dt_announce desc
```
