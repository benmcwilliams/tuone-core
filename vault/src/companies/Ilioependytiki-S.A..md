```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Ilioependytiki-S.A." or company = "Ilioependytiki S.A.")
sort location, dt_announce desc
```
