```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Asociación-Nuclear-Ascó-Vandellós-II-(ANAV)" or company = "Asociación Nuclear Ascó Vandellós II (ANAV)")
sort location, dt_announce desc
```
