```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Rubis-Photosol" or company = "Rubis Photosol")
sort location, dt_announce desc
```
