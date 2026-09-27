--SPDX-License-Identifier: AGPL-3.0-or-later
--Goddess of Whim (historical implementation, Retro Formats)
--Upstream: https://github.com/ProjectIgnis/CardScripts/blob/383bfbd62cefc0a28e075acfb78b0bb8203b94c7/official/c67959180.lua
--Copyright (C) 2020  Project Ignis contributors. See version history and author credit line for each file.
--Modified by edopro-retro-formats on 2026-09-27: removed the once-per-turn limit, which the 2012 erratum added; the effect description is read from the modern card's strings.
--This modified file is licensed, like its upstream, under the GNU Affero General
--Public License, version 3 or (at your option) any later version. The licence
--text is LICENSE-AGPL-3.0-or-later.txt next to this file in dist/scripts/, and
--LICENSES/AGPL-3.0-or-later.txt in the edopro-retro-formats repository.
--
--Period text: "Toss a coin and call Heads or Tails. Call it right and this card's ATK
--will be doubled during this turn. Call it wrong and it will be halved during this turn."
--
--See data/custom-cards/c600000004.json for what this script does not reproduce.
--きまぐれの女神
--Goddess of Whim
local s,id=GetID()
function s.initial_effect(c)
	--Toss a coin and either double or halve ATK
	local e1=Effect.CreateEffect(c)
	e1:SetDescription(aux.Stringid(67959180,0))
	e1:SetCategory(CATEGORY_COIN)
	e1:SetType(EFFECT_TYPE_IGNITION)
	e1:SetRange(LOCATION_MZONE)
	e1:SetTarget(s.target)
	e1:SetOperation(s.operation)
	c:RegisterEffect(e1)
end
s.toss_coin=true
function s.target(e,tp,eg,ep,ev,re,r,rp,chk)
	if chk==0 then return true end
	Duel.SetOperationInfo(0,CATEGORY_COIN,nil,0,tp,1)
end
function s.operation(e,tp,eg,ep,ev,re,r,rp)
	local c=e:GetHandler()
	if c:IsRelateToEffect(e) and c:IsFaceup() then
		local e1=Effect.CreateEffect(c)
		e1:SetType(EFFECT_TYPE_SINGLE)
		e1:SetCode(EFFECT_SET_ATTACK_FINAL)
		e1:SetReset(RESETS_STANDARD_DISABLE_PHASE_END)
		if Duel.CallCoin(tp) then
			e1:SetValue(c:GetAttack()*2)
		else
			e1:SetValue(c:GetAttack()/2)
		end
		c:RegisterEffect(e1)
	end
end